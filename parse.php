<?php

ini_set('display_errors', 'stderr');


function print_help(): void
{
	$help_message = "\nAnalyzátor kódu v IPPcode23\nAutor: Martin Soukup, xsouku15\n";
	$help_message .= "parse.php načte ze standardního vstupu zdrojový kód v IPPcode23 a\nvypíše na standardní výstup XML reprezentaci programu.\n";
	$help_message .= "Použití: php parse.php < vstupní_soubor\n";
	$help_message .= "Skript pracuje s těmito parametry: ";
	$help_message .= "--help - Zobrazí nápovědu.\n";
	$help_message .= "Návratové kódy:\n";
	$help_message .= "10 - chybějící parametr skriptu (je-li třeba) nebo použití zakázané kombinace parametrů.\n";
	$help_message .= "11 - chyba při otevírání vstupních souborů (např. neexistence, nedostatečné oprávnění).\n";
	$help_message .= "12 - chyba při otevření výstupních souborů pro zápis (např. nedostatečné oprávnění, chyba při zápisu).\n";
	$help_message .= "21 - chybná nebo chybějící hlavička ve zdrojovém kódu zapsaném v IPPcode23.\n";
	$help_message .= "22 - neznámý nebo chybný operační kód ve zdrojovém kódu zapsaném v IPPcode23.\n";
	$help_message .= "23 - jiná lexikální nebo syntaktická chyba zdrojového kódu zapsaného v IPPcode23\n";
	$help_message .= "99 - interní chyba (neovlivněná vstupními soubory či parametry příkazové řádky; např. chyba alokace paměti).\n";


	fwrite( STDOUT, $help_message);
	exit(0);

}

function write_param( string $param, int $order, string $type, XMLWriter $xw )
{
	//echo($param);
	xmlwriter_start_element( $xw, 'arg' . $order);
	xmlwriter_start_attribute( $xw, 'type' );
	xmlwriter_text( $xw, $type);
	xmlwriter_end_attribute( $xw );
	xmlwriter_text( $xw , $param );
	xmlwriter_end_element( $xw );

}

function process_instruction(string $opc , XMLWriter $xw , int $order ,string ...$params): void
{
	$arg_order = 0;
	xmlwriter_start_element( $xw, 'instruction');
	xmlwriter_start_attribute( $xw, 'order' );
	xmlwriter_text($xw, $order);
	xmlwriter_end_attribute( $xw );
	xmlwriter_start_attribute( $xw, 'opcode' );
	xmlwriter_text( $xw, $opc );
	xmlwriter_end_attribute( $xw );
	if( empty($params) )
	{
		xmlwriter_end_element( $xw );
		return;
	}

	foreach( $params as $param )
	{
		$arg_order++;
		if( preg_match("/(LF|GF|TF)@[a-zA-Z-_%!?#&*$][a-zA-Z-_%!?#&*$0-9]*/", $param))
		{
			write_param( $param, $arg_order, 'var', $xw);
		}
		elseif( preg_match("/[a-zA-Z-_%!?#&*$][a-zA-Z-_%!?#&*$0-9]*/", $param) )
		{
			write_param( $param, $arg_order, 'label', $xw);
		}
		elseif( preg_match("/nil@nil/", $param ) )
		{
			write_param( 'nil', $arg_order , 'nil' , $xw);
		}
		elseif( preg_match("/bool@(true|false)/", $param ) )
		{
			$bool = explode( "@", $param);
			write_param( $bool[1], $arg_order, $bool[0], $xw);
		}
		elseif( preg_match("/int@(-)?(0|[1-9][0-9]*|0[0-7]*|[0-9a-fA-F]+)/", $param) )
		{
			$int = explode( "@", $param);
			write_param( $int[1], $arg_order, $int[0], $xw);
		}
		elseif( preg_match("/string@([^\s#\\\]*(\\\[0-9]{3})*)*/", $param ) ) 
		{
			$string = explode( "@", $param, 2);
			write_param($string[1], $arg_order, $string[0], $xw);
		}
		elseif( preg_match("/(LF|GF|TF)@[a-zA-Z-_%!?#&*$][a-zA-Z-_%!?#&*$0-9]*/", $param) )
		{
			write_param( $param, $arg_order, 'var', $xw);	
		}
		else
		{
			fwrite( STDERR, $param . " je špatně zapsán");
			exit(23);
		}
		xmlwriter_end_element( $xw );
	}


}

function comment_out( string $line ): string
{
	return explode("#", $line)[0];
}

function findHeader( string $pline, XMLWriter $xw): bool
{
	if($pline == false)
	{
		return false;
	}
	if( preg_match( "/.IPPcode23/i", $pline))
		{
			xmlwriter_start_element( $xw, 'program' ); //Po nalezení hlavičky začíná kořenový element program s atributem language a hodnotou ippcode22
			xmlwriter_start_attribute( $xw, 'language' );
			xmlwriter_text( $xw, 'IPPcode23' );
			xmlwriter_end_attribute( $xw );
			return true;
		}
	else
	{

		fwrite( STDERR, "Chybějící nebo špatně zapsaná hlavička - kód chyby: 21");
		exit(21);
	}
}

if ( $argc > 1 )
{
	if( $argv[1] == '--help' && $argc === 2 )
		print_help();
	else
		exit(10); 
}
if( empty(STDIN) )
	exit(0);

$header_found = false;
$order = 0;

$xw = xmlwriter_open_memory();
xmlwriter_set_indent($xw,1);
$res = xmlwriter_set_indent_string($xw, ' ');
xmlwriter_start_document($xw, '1.0', 'UTF-8');

while( !feof(STDIN) )
{
	
	$line = fgets( STDIN );
	$line = preg_replace('/^\n+|^[\t\s]*\n+/m','',$line);

	
	$pline = comment_out( $line );

	if( !$header_found )
	{
		$header_found = findHeader( $pline, $xw );
	}
	else
	{
		$pline = preg_replace('/\s+/', ' ', $pline);

		$row = explode(" ", trim($pline, "\n"));

		if( empty( $row[0] ))
			continue;
		else
			$opc = strtoupper( $row[0] );
		
		$first = false;
		if( !empty( $row[1] ) )
		{
			$first = $row[1];
		}

		$second = false;
		if( !empty( $row[2]) )
		{
			$second = $row[2];
		}

		$third = false;
		if( !empty( $row[3]) )
		{
			$third = $row[3];
		}
		$order++;
		if( in_array( $opc, ['CREATEFRAME', 'PUSHFRAME', 'POPFRAME', 'RETURN', 'BREAK']))
		{
			if( $first != false)
			{
				fwrite( STDERR, "Instruce " . $opc . "musí být bez argumentů");
				exit(23);
			}

			process_instruction($opc, $xw, $order);
		}
		elseif( in_array( $opc, ['DPRINT', 'EXIT', 'JUMP', 'LABEL', 'WRITE', 'POPS', 'PUSHS', 'CALL', 'DEFVAR']))
		{
			if( $first == false)
			{
				fwrite( STDERR, "Instrukce" . $opc . "musí být aspoň jeden argument");
				exit(23);
			}

			process_instruction($opc, $xw, $order,$first);

		}
		elseif( in_array( $opc , ['MOVE','INT2CHAR','STRLEN', 'TYPE']))
		{
			if( $second == false)
			{
				fwrite( STDERR, "Instrukce" . $opc . "musí být aspoň dva argumenty");
				exit(23);
			}

			process_instruction($opc, $xw, $order,$first, $second);

		}
		elseif( in_array( $opc , ['JUMPIFNEQ', 'JUMPIFEQ', 'SETCHAR', 'GETCHAR', 'CONCAT', 'STRI2INT', 'AND', 'OR', 'NOT', 'LT', 'GT', 'EQ', 'IDIV', 'MUL', 'SUB', 'ADD']))
		{
			if( $third == false)
			{
				fwrite( STDERR, "Instrukce" . $opc . "musí být aspoň tři argumenty");
				exit(23);
			}

			process_instruction($opc, $xw, $order,$first, $second, $third);

		}
		else
		{
			fwrite( STDERR, "Instrukce " . $opc . " je neznámý nebo chybný operační kód ve zdrojovém kódu zapsaném v IPPcode23. ");
			exit(22);
		}

	}


}
xmlwriter_end_element( $xw );
fwrite( STDOUT, xmlwriter_output_memory($xw));
exit(0);
?>

