import starlink.Ast as Ast
import starlink.Grf as Grf
import matplotlib.pyplot as plt
import pyfits

"""
This module provides function and classes that wrap up sequences of PyAST
calls to perform commonly used operations. It requires the PyFITS and
matplotlib libraries to be installed.
"""

# ======================================================================
class PyFITSAdapter:
   """

   Adapter to allow PyAST FitsChan objects to read and write headers to
   and from a PyFITS HDU.

   This class allows a PyFITS HDU to be used as the source or sink object
   with a FitsChan.

   When used as a FitsChan source, the PyFITSAdapter will allow the
   FitsChan to read each of the cards in the associated PyFITS header,
   thus allowing the cards to be copied into the FitsChan. This happens
   when the newly created, empty FitsChan is used for the first time
   (i.e. when any of its methods is invoked), and subsequently whenever
   the FitsChan.readfits() method is invoked.

   When used as a FitsChan sink, the PyFITSAdapter will allow the
   FitsChan to copy its own header cards into the PyFITS header. This
   happens when the FitsChan is deleted or when the FitsChan.writefits()
   method is invoked. Each FitsChan card replaces any existing card in
   the PyFITS header that refers to the same keyword. If there is no card
   for the keyword already in the PyFITS header, the FitsChan card will
   be appended to the end of the header.

   """

   def __init__(self,hdu):
      """
      Construct a PyFITSAdapter for a specified PyFITS HDU.

      Parameters:
         hdu: An element of the hdulist associated with a FITS file
            opened using pyfits.open(). If the entire hdulist is supplied,
            rather than an element of the hdulist, then the primary HDU
            (element zero) will be used.

      Examples:
         - To read WCS from the 'DATA' extension in FITS file 'test.fit':

         >>> import pyfits
         >>> import starlink.Ast as Ast
         >>> import starlink.Atl as Atl
         >>>
         >>> hdulist = pyfits.open('test.fit')
         >>> fc = Ast.FitsChan( Atl.PyFITSAdapter( hdulist['DATA'] ) )
         >>> framset = fc.read()

         - To write a FrameSet to the primary HDU in FITS file 'old.fit',
         using standard FITS-WCS keywords:

         >>> import pyfits
         >>> import starlink.Ast as Ast
         >>> import starlink.Atl as Atl
         >>>
         >>> hdulist = pyfits.open('old.fit')
         >>> fc = Ast.FitsChan( None, Atl.PyFITSAdapter( hdulist ) )
         >>> if fc.write( framset ) == 0:
         >>>    print("Failed to convert FrameSet to FITS header")
      """

#  If the supplied object behaves like a sequence, use element zero (the
#  primary HDU). Otherwise use the supplied object.
      try:
         self.hdu = hdu[ 0 ]
      except TypeError:
         self.hdu = hdu

#  Initialise the index of the next card to read or write.
      self.index = 0


# -----------------------------------------------------------------
   def astsource(self):

      """
      This method is called by the FitsChan to obtain a single 80-character
      FITS header card. It iterates over all the cards in the PyFITS
      header, returning each one in turn. It then returns "None" to
      indicate that there are no more header cards to read.
      """

      if self.index < len( self.hdu.header.ascard ):
         result = self.hdu.header.ascard[ self.index ].ascardimage()
         self.index += 1
      else:
         result = None
         self.index = 0

      return result

# -----------------------------------------------------------------
   def astsink(self,card):

      """
      This method is called by the FitsChan to store a single 80-character
      FITS header card. If the header already contains a card for
      the keyword, the existing card is replaced with the new card.
      Otherwise, the new card is stored at the end of the header.
      """

      card = pyfits.core.Card.fromstring(card)
      self.hdu.header.update( card.key, card.value, card.comment )



# ======================================================================
def readfitswcs( hdu ):

   r"""Reads an AST FrameSet from a FITS header.

      The header from the specified FITS HDU is read, and an AST FrameSet
      describing the WCS information in the header is returned. None is
      returned instead of a FrameSet if WCS information cannot be read
      from the header. A string identifying the scheme used to describe
      WCS information in the header (the encoding) is also returned.

      (frameset,encoding) = starlink.Atl.readfitswcs( hdu )

      Parameters:
         hdu: An element of the hdulist associated with a FITS file
 	    opened using pyfits.open(). If the entire hdulist is supplied,
 	    rather than an element of the hdulist, then the primary HDU
 	    (element zero) will be used.
         frameset: A reference to the FrameSet describing the pixel and
	    world coordinate systems read from the FITS header, or "None"
	    if no WCS could be read.
         encoding: Indicates how the WCS information was encoded in the
	    header. For possible values, see the documentation for the
	    "Encoding" attribute in SUN/211.

      Example:
         >>> import pyfits
         >>> import starlink.Atl as Atl
         >>>
         >>> hdulist = pyfits.open( 'test.fit' )
         >>> (frameset,encoding) = Atl.readfitswcs( hdulist[ 3 ] )
         >>> if frameset == None:
         >>>    print( "Cannot read WCS from test.fit" )

   """

   try:
      myhdu = hdu[ 0 ]
   except TypeError:
      myhdu = hdu

   fitschan = Ast.FitsChan( PyFITSAdapter( myhdu ) )
   encoding = fitschan.Encoding
   frameset = fitschan.read()
   return (frameset,encoding)




# ======================================================================
def writefitswcs( frameset, hdu, encoding="FITS-WCS" ):

   r"""Write an AST FrameSet to a FITS file.

      The WCS information described by the supplied FrameSet is converted
      into a set of FITS header cards which are stored in the supplied
      HDU (all cards in the header are first removed).

      nobj = starlink.Atl.writefitswcs( frameset, hdu, encoding="FITS-WCS" )

      Parameters:
         frameset: A reference to the FrameSet to be written out to the
            FITS header.
         hdu: An element of the PyFITS hdulist associated with a FITS file.
            The header cards generated from the FrameSet are stored in the
            header associated with this HDU. All cards are first removed
            from the header. If an entire hdulist is supplied, rather than
            an element of the hdulist, then the primary HDU (element zero)
            will be used.
         encoding: Indicates how the WCS information is to be encoded in the
	    header. For possible values, see the documentation for the
	    "Encoding" attribute in SUN/211.
         nobj:
            Returned equal to 1 if the FrameSet was converted successfully
            to FITS headers using the requested encoding, and zero
            otherwise.
      Example:
         >>> import starlink.Atl as Atl
         >>>
         >>> (frameset,encoding) = Atl.readfitswcs( hdu1 )
         >>> if Atl.writefitswcs( frameset, hdu2, encoding="FITS-AIPS" ) == 0:
         >>>    print( "Cannot convert WCS to FITS-AIPS encoding" )

    """

   fitschan = Ast.FitsChan( None, PyFITSAdapter(hdu) )
   fitschan.Encoding = encoding
   return fitschan.write( frameset )



# ======================================================================
def plotframeset( axes, gbox, bbox, frameset, options="" ):
   r"""Plot an annotated coordinate grid in a matplotlib axes area.

      plot = starlink.Atl.plotframeset( axes, gbox, bbox, frameset,
                                        options="" )

      Parameters:
         axes: A matplotlib "Axes" object. The annotated axes normally
            produced by matplotlib will be removed, and axes will
            instead be drawn by the AST Plot class.
         gbox: A list of four values giving the bounds of the new
            annotated axes within the matplotlib Axes object. The supplied
            values should be in the order (xleft,ybottom,xright,ytop) and
            should be given in the matplotlib "axes" coordinate system.
         bbox: A list of four values giving the bounds of the new
            annotated axes within the coordinate system represented by the
            base Frame of the supplied FrameSet. The supplied values should
            be in the order (xleft,ybottom,xright,ytop).
         frameset: An AST FrameSet such as returned by the Atl.readfitswcs
            function. Its base Frame should be 2-dimensional.
         options: An optional string holding a comma-separated list of Plot
            attribute settings. These control the appearance of the
            annotated axes.
         plot: A reference to the Ast.Plot that was used to draw the axes.

      Example:
         >>> import pyfits
         >>> import starlink.Atl as Atl
         >>> import matplotlib.pyplot
         >>>
         >>> hdulist = pyfits.open( 'test.fit' )
         >>> (frameset,encoding) = starlink.Atl.readfitswcs( hdulist[0] )
         >>> if frameset != None:
         >>>    naxis1 = hdulist[0].header['NAXIS1']
         >>>    naxis2 = hdulist[0].header['NAXIS2']
         >>>    Atl.plotframeset( matplotlib.pyplot.figure().add_subplot(111),
         >>>                      [ 0.1, 0.1, 0.9, 0.9 ],
         >>>                      [ 0.5, 0.5, naxis1+0.5, naxis2+0.5 ], frameset )
         >>>    matplotlib.pyplot.show()
   """

   axes.xaxis.set_visible( False )
   axes.yaxis.set_visible( False )

   plot = Ast.Plot( frameset, gbox, bbox, Grf.grf_matplotlib( axes ), options )
   plot.grid()
   return plot



# ======================================================================
def plotfitswcs( axes, gbox, hdu, options="" ):

   r"""Read WCS from a PyFITS HDU and plot an annotated coordinate grid
      in a matplotlib axes area. The grid covers the entire image.

      plot = starlink.Atl.plotfitswcs( axes, gbox, hdu, options="" )

      Parameters:
         axes: A matplotlib "Axes" object. The annotated axes normally
            produced by matplotlib will be removed, and axes will
            instead be drawn by the AST Plot class.
         gbox: A list of four values giving the bounds of the new
            annotated axes within the matplotlib Axes object. The supplied
            values should be in the order (xleft,ybottom,xright,ytop) and
            should be given in the matplotlib "axes" coordinate system.
         hdu: An element of the hdulist associated with a FITS file
 	    opened using pyfits.open(). If the entire hdulist is supplied,
 	    rather than an element of the hdulist, then the primary HDU
 	    (element zero) will be used.
         options: An optional string holding a comma-separated list
            of Ast.Plot attribute settings. These control the appearance
            of the annotated axes.
         plot: A reference to the Ast.Plot that was used to draw the axes.

      Example:
         >>> import pyfits
         >>> import starlink.Atl as Atl
         >>> import matplotlib.pyplot
         >>>
         >>> hdulist = pyfits.open( 'test.fit' )
         >>> Atl.plotfitswcs( matplotlib.pyplot.figure().add_subplot(111),
         >>>                  [ 0.1, 0.1, 0.9, 0.9 ], hdulist )
         >>> matplotlib.pyplot.show()
   """

   try:
      myhdu = hdu[ 0 ]
   except TypeError:
      myhdu = hdu

   (frameset,encoding) = readfitswcs( myhdu )
   naxis1 = myhdu.header[ 'NAXIS1' ]
   naxis2 = myhdu.header[ 'NAXIS2' ]
   return plotframeset( axes, gbox, [ 0.5, 0.5, naxis1+0.5, naxis2+0.5 ],
                        frameset, options )

